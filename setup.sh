echo "Install thirdparty compunents using install.sh script in thirdparty folder"

exit 0


ls /usr/local/bin/brew || ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" < /dev/null 2> /dev/null

ls /usr/local/lib/libraw.* || brew install libraw

ls /usr/local/bin/ffmpeg || brew install ffmpeg

ls /usr/local/bin/gifsicle || brew install gifsicle

# following is not used by photosync, but can be used to check hash.md5 files
ls /usr/local/bin/md5sum || brew install md5sha1sum
