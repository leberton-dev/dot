package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestInstallLink(t *testing.T) {
	tests := []struct {
		name       string
		setup      func(source string, dest string) error
		wantBackup bool
	}{
		{"missing", func(source string, dest string) error { return nil }, false},
		{"linked", func(source string, dest string) error { return os.Symlink(source, dest) }, false},
		{"wrong target", func(source string, dest string) error { return os.Symlink("/other", dest) }, true},
		{"real file", func(source string, dest string) error { return os.WriteFile(dest, []byte("x"), 0644) }, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dir := t.TempDir()
			backDir := t.TempDir()
			configPath := filepath.Join(dir, "dotfiles.toml")
			link := Link{Source: "src", Dest: filepath.Join(dir, "dest")}
			source := filepath.Join(dir, "src")

			err := tt.setup(source, link.Dest)
			if err != nil {
				t.Fatalf("setup: %s", err)
			}

			err = installLink(link, configPath, backDir)
			if err != nil {
				t.Fatalf("installLink: %s", err)
			}

			got, err := linkStatus(link, configPath)
			if err != nil {
				t.Fatalf("linkStatus: %s", err)
			}
			if got != Linked {
				t.Errorf("after install: got %s, want linked", got)
			}

			backPath := filepath.Join(backDir, link.Dest)
			_, err = os.Lstat(backPath)
			if tt.wantBackup && err != nil {
				t.Errorf("backup missing at %s: %s", backPath, err)
			}
		})
	}
}
