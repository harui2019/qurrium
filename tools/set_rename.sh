# Rename the project from qurry to qurrium

echo "| Release type: $1"

if [ "$2" = 'test' ]; then
    echo "| Test mode: ON"
elif [ "$2" != '' ]; then
    echo "| Test mode: OFF"
    echo "| Usage: $0 <release_type> [test]"
    exit 1
fi

echo "| Script executed from: ${PWD}"
BASEDIR=$(dirname "$0")
echo "| Script location: ${BASEDIR}"

if [ "$1" = "nightly" ]; then
    python "${BASEDIR}/set_version.py" --release nightly $([ "$2" = 'test' ] && echo '--test')
    python "${BASEDIR}/set_pyproject_qurry.py" --release nightly
elif [ "$1" = "stable" ]; then
    python "${BASEDIR}/set_version.py" --release stable $([ "$2" = 'test' ] && echo '--test')
    python "${BASEDIR}/set_pyproject_qurry.py" --release stable
else
    echo "| Invalid release type: $1"
    echo "| Usage: $0 <release_type> [test]"
    echo "| Options: nightly, stable"
    exit 1
fi
