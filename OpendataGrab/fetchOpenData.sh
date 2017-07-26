#!/bin/bash
BASE_URL="https://opendata.dwd.de/weather/local_forecasts/"
CONTENT_LOG="content.log"
CONTENT_LOG_BZ2="$CONTENT_LOG.bz2"
CONTENT_LOG_OLD="$CONTENT_LOG.old"
TMP_BASE="fetchOpenData"
TODO_LIST="$TMP_BASE.todo"
LOCK_FILE="$TMP_BASE.lock"

WGET="/usr/bin/wget"
BUNZIP2="/usr/bin/bunzip2"

if [ -f $LOCK_FILE ]
then
   echo "Script already running!"
   exit 1
fi

# Handle signals
trap 'exithandler' 0 1 2 15
exithandler() {
   rm -f $LOCK_FILE $TODO_LIST $CONTENT_LOG
}

echo "$$" > $LOCK_FILE
$WGET -q -O - ${BASE_URL}${CONTENT_LOG_BZ2} | $BUNZIP2 | grep -v $CONTENT_LOG_BZ2 > $CONTENT_LOG

if ! [ -f $CONTENT_LOG ]
then
   echo "Download failed"
   exit 1
fi

if [ -f $CONTENT_LOG_OLD ]
then
   diff $CONTENT_LOG $CONTENT_LOG_OLD | grep "<" | sed s/\<\ .// | cut -f 1 -d "|" | sed "s,^\/,$BASE_URL," > $TODO_LIST
else
   cat $CONTENT_LOG | cut -f 1 -d "|" | sed "s,^.\/,$BASE_URL," > $TODO_LIST
fi

if [ -s $TODO_LIST ]
then
   $WGET -q -x -np -i $TODO_LIST
fi

mv $CONTENT_LOG $CONTENT_LOG_OLD

exit 0
