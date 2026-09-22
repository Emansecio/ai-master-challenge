package config

import (
	"bufio"
	"os"
	"strings"
)

// Environment has precedence; this reader never logs values.
func Load(path string) error {
	f, e := os.Open(path)
	if os.IsNotExist(e) {
		return nil
	}
	if e != nil {
		return e
	}
	defer f.Close()
	s := bufio.NewScanner(f)
	for s.Scan() {
		line := strings.TrimSpace(strings.TrimPrefix(s.Text(), "\ufeff"))
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		key, value, ok := strings.Cut(line, "=")
		if ok && os.Getenv(key) == "" {
			os.Setenv(key, strings.Trim(value, "\"'"))
		}
	}
	return s.Err()
}
