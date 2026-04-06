"""Unit tests for infra/utils.py."""



from infra import utils


class TestGetTerminalSize:
    def test_returns_tuple(self):
        cols, lines = utils.get_terminal_size()
        assert isinstance(cols, int)
        assert isinstance(lines, int)
        assert cols >= 80
        assert lines >= 24


class TestGetVisibleLength:
    def test_plain_text(self):
        assert utils.get_visible_length("hello") == 5

    def test_ansi_colored(self):
        colored = "\033[92mgreen\033[0m"
        assert utils.get_visible_length(colored) == 5

    def test_ansi_blink(self):
        blink = "\033[91m\033[5mblink\033[0m"
        assert utils.get_visible_length(blink) == 5

    def test_empty_string(self):
        assert utils.get_visible_length("") == 0

    def test_ansi_only(self):
        assert utils.get_visible_length("\033[0m") == 0


class TestFormatBytes:
    def test_zero(self):
        assert "0.00" in utils.format_bytes(0)

    def test_kilobytes(self):
        result = utils.format_bytes(1024)
        assert "K" in result

    def test_megabytes(self):
        result = utils.format_bytes(1024 * 1024)
        assert "M" in result

    def test_gigabytes(self):
        result = utils.format_bytes(1024 * 1024 * 1024)
        assert "G" in result

    def test_width(self):
        result = utils.format_bytes(1024, width=15)
        assert len(result) == 15


class TestCreateProgressBar:
    def test_zero_percent(self):
        bar = utils.create_progress_bar(0.0, width=10)
        assert "▕" in bar and "▏" in bar

    def test_full_percent(self):
        bar = utils.create_progress_bar(100.0, width=10)
        filled = bar.count("█")
        assert filled == 10

    def test_half_percent(self):
        bar = utils.create_progress_bar(50.0, width=10)
        filled = bar.count("█")
        assert filled == 5

    def test_above_threshold_color(self):
        bar = utils.create_progress_bar(95.0, threshold_key="cpu")
        assert "\033[91m" in bar  # red

    def test_below_threshold_color(self):
        bar = utils.create_progress_bar(50.0, threshold_key="cpu")
        assert "\033[92m" in bar  # green


class TestDrawBoxLine:
    def test_left_align(self):
        line = utils.draw_box_line("hello", 20, "left")
        assert line.startswith("│ ")
        assert line.endswith(" │")
        assert "hello" in line

    def test_center_align(self):
        line = utils.draw_box_line("hi", 20, "center")
        assert line.startswith("│ ")
        assert line.endswith(" │")

    def test_right_align(self):
        line = utils.draw_box_line("end", 20, "right")
        assert line.startswith("│ ")
        assert line.endswith(" │")

    def test_ansi_content(self):
        content = "\033[92mgreen\033[0m"
        line = utils.draw_box_line(content, 20)
        assert "green" in line


class TestLogMessage:
    def test_log_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("infra.config.CACHE_DIR", str(tmp_path))
        # Create new FileLogger instance that picks up the mocked CACHE_DIR
        logger = utils.FileLogger(log_dir=str(tmp_path))
        logger.log("test", "hello", "INFO")
        log_file = tmp_path / "coresight.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "test" in content
        assert "hello" in content
        assert "INFO" in content

    def test_log_level_filtering(self, tmp_path, monkeypatch):
        monkeypatch.setattr("infra.config.CACHE_DIR", str(tmp_path))
        monkeypatch.setattr("infra.config.LOG_LEVEL", "WARNING")
        utils.log_message("test", "debug msg", "DEBUG")
        log_file = tmp_path / "coresight.log"
        if log_file.exists():
            assert "debug msg" not in log_file.read_text()


class TestClearScreen:
    def test_no_exception(self):
        utils.clear_screen()  # Should not raise


class TestTerminalFormatter:
    def test_instance(self):
        f = utils.TerminalFormatter()
        assert f.get_visible_length("test") == 4

    def test_progress_bar(self):
        f = utils.TerminalFormatter()
        bar = f.create_progress_bar(50.0, width=10)
        assert bar.count("█") == 5

    def test_draw_box_line(self):
        f = utils.TerminalFormatter()
        line = f.draw_box_line("test", 20)
        assert line.startswith("│ ")
        assert line.endswith(" │")


class TestFileLogger:
    def test_log(self, tmp_path):
        logger = utils.FileLogger(log_dir=str(tmp_path))
        logger.log("mymod", "test msg", "WARNING")
        log_file = tmp_path / "coresight.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "mymod" in content
        assert "test msg" in content
        assert "WARNING" in content

    def test_custom_filename(self, tmp_path):
        logger = utils.FileLogger(log_dir=str(tmp_path), log_file_name="custom.log")
        logger.log("m", "msg")
        assert (tmp_path / "custom.log").exists()
