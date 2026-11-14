package main

import (
	"errors"
	"io/fs"
	"os"
)

type LinkStatus int

const (
	Unknown LinkStatus = iota
	Missing
	Linked
	WrongTarget
	RealFile
)

func (s LinkStatus) String() string {
	switch s {
	case Missing:
		return "missing"
	case Linked:
		return "linked"
	case WrongTarget:
		return "wrong target"
	case RealFile:
		return "real file"
	}
	return "unknown"
}

func linkStatus(link Link, configPath string) (LinkStatus, error) {
	dest, err := destPath(link.Dest)
	if err != nil {
		return Unknown, err
	}
	info, err := os.Lstat(dest)
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			return Missing, nil
		}
		return Unknown, err
	}

	if info.Mode()&os.ModeSymlink != 0 {
		source, err := sourcePath(configPath, link.Source)
		if err != nil {
			return Unknown, err
		}
		destLink, err := os.Readlink(dest)
		if err != nil {
			return Unknown, err
		}
		if destLink == source {
			return Linked, nil
		}
		return WrongTarget, nil
	}
	return RealFile, nil
}
