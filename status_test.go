package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLinkStatus(t *testing.T) {
	tests := []struct {
		name  string
		setup func(source string, dest string) error
		want  LinkStatus
	}{
		{"missing", func(source string, dest string) error { return nil }, Missing},
		{"linked", func(source string, dest string) error { return os.Symlink(source, dest) }, Linked},
		{"wrong target", func(source string, dest string) error { return os.Symlink("/other", dest) }, WrongTarget},
		{"real file", func(source string, dest string) error { return os.WriteFile(dest, []byte("x"), 0644) }, RealFile},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dir := t.TempDir()
			configPath := filepath.Join(dir, "dotfiles.toml")
			link := Link{Source: "src", Dest: filepath.Join(dir, "dest")}
			source := filepath.Join(dir, "src")

			err := tt.setup(source, link.Dest)
			if err != nil {
				t.Fatalf("setup: %s", err)
			}

			got, err := linkStatus(link, configPath)
			if err != nil {
				t.Fatalf("linkStatus: %s", err)
			}
			if got != tt.want {
				t.Errorf("got %s, want %s", got, tt.want)
			}
		})
	}
}
