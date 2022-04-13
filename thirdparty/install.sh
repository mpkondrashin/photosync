#!/bin/sh
set -e

MY_DIR="$(cd "$(dirname $0)"; pwd)"

ROOT="${MY_DIR}/root"
mkdir -p "${ROOT}"
echo "Folder for third party components binaries" > "${ROOT}/README.txt"

BUILD="${MY_DIR}/build"
mkdir -p "${BUILD}"
echo "Folder for building components" > "${BUILD}/README.txt"

exiftool()
{
  if [ -x ${ROOT}/exiftool ]
  then
    echo "exiftool is installed - skip"
    return
  fi
  git clone https://github.com/exiftool/exiftool.git
  cd exiftool
  perl Makefile.PL
  make
  make test
  mkdir ${ROOT}/exiftool
  cp exiftool ${ROOT}/exiftool
  cp -R blib/lib ${ROOT}/exiftool
}

ffmpeg()
{
  if [ -x ${ROOT}/bin/ffmpeg ]
  then
    echo "ffmpeg is installed - skip"
    return
  fi
	git clone https://git.ffmpeg.org/ffmpeg.git
	cd ffmpeg
	./configure --prefix="${ROOT}"
	make
	make install
}

gifsicle()
{
  if [ -x ${ROOT}/bin/gifsicle ]
  then
    echo "gifsicle is installed - skip"
    return
  fi
  #git clone https://github.com/kohler/gifsicle.git
  GIFSICLE=gifsicle-1.93
  curl -O http://www.lcdf.org/gifsicle/${GIFSICLE}.tar.gz
  tar xfvz ${GIFSICLE}.tar.gz
  cd ${GIFSICLE}
  ./configure --prefix="${ROOT}"
  make
  make install
}

libraw()
{
  if ls "${ROOT}"/lib/libraw* 1> /dev/null 2>&1
  then
    echo "libraw is installed - skip"
    return
  fi
  # Taken from: https://pypi.org/project/rawpy/
  git clone https://github.com/LibRaw/LibRaw.git libraw
  git clone https://github.com/LibRaw/LibRaw-cmake.git libraw-cmake
  cd libraw
  git checkout 0.20.0
  cp -R ../libraw-cmake/* .
  cmake -DMAKE_INSTALL_PREFIX=${ROOT} .
  make -DMAKE_INSTALL_PREFIX=${ROOT} 
  make install -DMAKE_INSTALL_PREFIX=${ROOT} 
}

echo "PhotoSync - install thirdparty components"

case "x$1" in
  "xinstall")
    echo "Target folder: ${ROOT}"
    cd ${BUILD}
    (exiftool)
    (ffmpeg)
    (gifsicle)
    (libraw)
    ;;
  "xcleanup")
    rm -rf ${BUILD}
    echo "Cleanup done"
    ;;
  *)
    echo "Usage ${0} {install|cleanup}"
    ;;
esac
