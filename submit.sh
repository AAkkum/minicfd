#! /bin/bash 

set -eu

lbCloneBase="${PWD}"
lbName='leaderboard-repo'
submitterName="anonymous-$(cksum <<< "$PWD" | cut -f 1 -d ' ')"
submitToRepo=false

function print_usage {
  echo "Submit script for the performance engineering practical course leaderboard."
  echo -e "-n\t\tThe name to be shown for this submission. Please use *only one* name, defaults to 'anonymous'."
  echo -e "-s\t\tSubmits the results into the repository."
  echo -e "-r\t\tPath to SLURM output file containing the MiniCFD time measurements"
}

function clone_repo_if_not_present {
  if [ ! -d "$lbName" ]; then
    git clone https://studi:glpat-p9g6feU-i2ouy2MB4w9hwm86MQp1OjFmcGYK.01.100x65fk0@git.rwth-aachen.de/tuda-sc/peng-praktikum/ws25-26/performance-challenge-leaderboard.git "$lbName"
  fi
}

function show_pending_changes {
  cd "${lbName}" || exit 1
  git pull --ff-only
  git status
  cd ..
}

function submit_to_repo {
  newFile="${1}"

  cd "${lbName}" || exit 1
  git pull --ff-only || exit 1
  git add -u || exit 1
  git add "${newFile}"
  git commit -m 'Adds new result' || exit 1
  git push || exit 1
  cd .. || exit 1
}

while getopts ":n:hsr:" opt; do
  case $opt in
    h)
      print_usage
      exit 0
      ;;
    r)
      value=$OPTARG
      echo "Value for option r: ${value}"
      resultfile=${value}
      ;;
    n)
      value=$OPTARG
      echo "Value for option n: ${value}"
      submitterName=${value}
      ;;
    s)
      echo "Submit to the repository"
      submitToRepo=true
      ;;
    \?)
      echo "Invalid option."
      print_usage
      exit 1
      ;;
  esac
done

if [[ ! -f "${resultfile}" ]]; then
    echo "result file does not exist on your filesystem."
    exit 1
fi

timings=$(grep -oP '\d+:\d+\.\d+elapsed' $resultfile | sed 's/elapsed//' | awk -F: '{ print ($1 * 60) + $2 }')
average=$(echo $timings | python -c 'print((lambda nums: f"{sum(nums)/len(nums):.2f}")((list(map(float, input().split())))))')
stdev=$(echo $timings | python -c 'print((lambda nums: f"{(sum((x - sum(nums)/len(nums))**2 for x in nums)/len(nums))**0.5:.2f}")((list(map(float, input().split())))))')

echo "average              $average"
echo "std. dev.            $stdev"

clone_repo_if_not_present

echo $average,$stdev > $lbName/task-3/${submitterName}

show_pending_changes

if $submitToRepo; then
  submit_to_repo "${lbCloneBase}/${lbName}/task-3/${submitterName}"
fi
