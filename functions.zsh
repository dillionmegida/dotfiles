function delb() {
    # support multiline paste: collect all args or stdin
    if [[ ! -t 0 ]]; then
        python3 "$DOTFILES_DIR/dotfiles/scripts/del_branches.py" "$@"
    else
        python3 "$DOTFILES_DIR/dotfiles/scripts/del_branches.py" "$@"
    fi
}


function dot() {
    local quiet=false
    if [[ "$1" == "-q" || "$1" == "--quiet" ]]; then
        quiet=true
        shift
    fi
  local dotfiles="$DOTFILES_DIR/dotfiles"
  local dirty=$(git -C "$dotfiles" status --porcelain)

  [[ "$quiet" == true ]] || box start "🔄 pulling... "
  [[ "$quiet" == true ]] || box line ""

  if [[ -n "$dirty" ]]; then
      git -C "$dotfiles" stash -u &>/dev/null
      git -C "$dotfiles" pull &>/dev/null
      git -C "$dotfiles" stash pop &>/dev/null
  else
      git -C "$dotfiles" pull &>/dev/null
  fi

  source ~/.zshrc
  [[ "$quiet" == true ]] || box end "✅ reloaded"
}

function last() {
    local cmd=$(history | grep "$*" | grep -v "last $*" | tail -1 | sed 's/^ *[0-9]* *//')
    if [[ -z "$cmd" ]]; then
        box "No history found for: $*"
        return 1
    fi
    box "⏮  $cmd"
    eval "$cmd"
}

function box() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/boxprint.py" "$@"
}

function ignore() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/gitignore_local.py" "$@"
}

function uncommit {
  python3 "$DOTFILES_DIR/dotfiles/scripts/uncommit.py" "$@"
}

function stale {
  python3 "$DOTFILES_DIR/dotfiles/scripts/stale_branches.py" "$@"
}

# Time any command
function t() {
    local start=$EPOCHREALTIME
    eval "$@"
    local elapsed=$(( EPOCHREALTIME - start ))
    printf "\n⏱  Finished in %.2fs\n" $elapsed
}

function dev {
  if (( $+commands[devin-desktop] )); then
    devin-desktop "$@"
  else
    echo "devin-desktop not found" >&2
    return 1
  fi
}

# grep with default options
function s {
  if [[ $# -eq 0 ]]; then
    echo "Usage: s <pattern> [file...]"
    echo "       ... | s <pattern>"
    return 1
  elif [[ -t 0 ]]; then
    # No stdin input, use recursive grep
    grep -r -n -i --color=auto "$@"
  else
    # Has stdin input, use regular grep
    grep -n -i --color=auto "$@"
  fi
}

# get a particular line from output
function line {
  local lineno=$1
  sed -n "${lineno}p"
}

# find files
function ff {
  local search_dir="${1:-.}"
  local filename="${2:-*}"
  local depth="${3}"

  if [[ -z "$depth" ]]; then
    find "$search_dir" -type f -name "${filename}*"
  else
    find "$search_dir" -type f -maxdepth "$depth" -name "${filename}*"
  fi
}

# git log
function gl {
  if [[ $# -eq 0 ]]; then
    git --no-pager log -1
  else
    git --no-pager log -"$1"
  fi
}

function lab() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/lab.py" "$@"
}

function sym() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/sym.py" "$@"
}

function reb-edit() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/rebase_edit.py" "$@"
}

function capture() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/capture.py" "$@"
}

function fixup() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/fixup.py" "$@"
}

function blame() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/blame.py" "$@"
}

function help() {
    python3 "$DOTFILES_DIR/dotfiles/scripts/help.py" "$@"
}