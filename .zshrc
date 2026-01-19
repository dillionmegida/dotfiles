[ -f ~/zshrc_default ] && source ~/zshrc_default

export ZSH="$HOME/.oh-my-zsh"

#theme
ZSH_THEME="robbyrussell"

source $ZSH/oh-my-zsh.sh

# git aliases
alias g="git"
alias ga="git add"
alias gc="git checkout"
alias gcom="git commit -m"
alias gs="git status"
alias gb="git branch"
alias gps="git push"
alias greb="git rebase"
alias gc="git checkout"
alias gcb="git checkout -b"
alias gst="git stash -u"
alias gstp="git stash pop"
alias gnoedit="git commit --amend --no-edit"

alias c="pbcopy"
alias arg="xargs"

# custom functions
# git log
gl() {
  if [[ $# -eq 0 ]]; then
    git --no-pager log -1
  else
    git log "$@"
  fi
}

# find files
ff() {
  local search_dir="${1:-.}"
  local filename="${2:-*}"
  local depth="${3}"

  if [[ -z "$depth" ]]; then
    find "$search_dir" -type f -name "${filename}*"
  else
    find "$search_dir" -type f -maxdepth "$depth" -name "${filename}*"
  fi
}

# get a particular line from output
line() {
  local lineno=$1
  sed -n "${lineno}p"
}

alias nr="npm run"
alias ni="npm install"
alias nid="npm install -D" 
alias nu="npm uninstall"
alias nt="npm test"


co() {
  # Use the provided argument, or default to the current directory
  local target=$(realpath "${1:-$(pwd)}")

  echo "Opening VSCodium for: $target"
  open "vscodium://file/$target?window=new"
}

# Added by Windsurf
export PATH="/Users/dillion/.codeium/windsurf/bin:$PATH"
alias su="surf"