from PySide6.QtCore import QTimer

from app.config import config
from app.services.search_service import SearchResult, search_service


class SearchMixin:
    def _setup_search(self):
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._search_worker = None
        self._last_search_keyword = ""

    def _on_search_input(self, text: str):
        self._last_search_keyword = text.strip()
        self._search_timer.stop()
        if not self._last_search_keyword:
            self._clear_search_results()
            return
        self._search_timer.start(config.search_debounce_ms)

    def _do_search(self):
        keyword = self._last_search_keyword
            self._clear_search_results()
            return
        search_id, worker = search_service.search_async(keyword, config.search_case_insensitive)
        worker.setParent(None)
        worker.results_ready.connect(self._on_search_results_ready)
        worker.finished.connect(worker.deleteLater)
        worker.start()
        self._search_worker = worker

    def _on_search_results_ready(self, search_id: int, results: list[SearchResult]):
        if search_id != search_service.get_current_search_id():
            return
        if not self._last_search_keyword:
            self._clear_search_results()
            return
        self._display_search_results(results, self._last_search_keyword)

    def _clear_search_results(self):
        raise NotImplementedError

    def _display_search_results(self, results, keyword):
        raise NotImplementedError
