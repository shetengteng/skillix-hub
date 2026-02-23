(function() {
  var events = window.__WAB_EVENTS__ || [];
  window.__WAB_EVENTS__ = [];
  return JSON.stringify(events);
})();
