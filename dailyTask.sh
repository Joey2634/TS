#!/bin/bash
if [ $1 = 'orderMock' ];then
  python3 /home/gitlab-runner/ai-investment-manager/main/mock/sendOrder.py
elif [ $1 = 'clearMock' ];then
  python3 /home/gitlab-runner/ai-investment-manager/main/mock/runClearSettle.py
elif [ $1 = 'marketData' ];then
  python3 /home/gitlab-runner/ai-investment-manager/marketData/wind/DailyPickleWindData.py
elif [ $1 = 'selection' ];then
  python3 /home/gitlab-runner/ai-investment-manager/main/runSelection.py
elif [ $1 = 'orderLive' ];then
  python3 /home/gitlab-runner/ai-investment-manager/main/live/sendOrder.py
elif [ $1 = 'clearLive' ];then
  python3 /home/gitlab-runner/ai-investment-manager/main/live/runClearSettle.py
elif [ $1 = 'sentiment' ];then
  python3 /home/gitlab-runner/ai-investment-manager/selection/selectionCondition/SENTIMENT.py
elif [ $1 = 'windcode' ];then
  python3 /home/gitlab-runner/ai-investment-manager/marketData/wind/update_windcode.py
elif [ $1 = 'storeAccountFirst' ];then
  python3 /home/gitlab-runner/ai-investment-manager/main/mock/storeEodData.py
else
  echo "no action"
fi
