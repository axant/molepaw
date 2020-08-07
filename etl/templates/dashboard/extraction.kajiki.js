var ExtractionsEditor = Ractive.extend({
  template: '#Extractions_template',
  data: {},
  oninit: function () {
    var self = this;
    self.updateExtractions();
  },
  updateExtractions: function () {
    var self = this;
    self.set('loaded', false);
    $$.get("${tg.url(['/dashboard/extractions', str(dashboard.uid)])}", function (res) {
      var extractions = [];
      res.dashboard.extractions.forEach(function (e) {
	var extraction = {};
	extraction.uid = e.uid;
	extraction.index = e.index;
	extraction.extraction_id = e.extraction_id;
	extraction.visualization = e.visualization;
	extraction.graph_axis = e.graph_axis;
	extraction.name = e.extraction.name;
	extractions.push(extraction);
      })
      extractions.sort(function (a, b) {
	return a.index > b.index;
      })
      self.set('extractions', extractions);
      self.set('loaded', true);
      self.set('extractions_length_at_last_update', self.get('extractions').length);
    });
  },
  checkSaved: function () {
    var self = this;
    return self.get('extractions_length_at_last_update') == self.get('extractions').length;
  },
  addExtraction: function () {
    var self = this;
    var index = 0;
    if (self.get('extractions').length)
      index = self.get('extractions')[self.get('extractions').length - 1].index + 1;
    self.push('extractions', {
      'editing': true,
      'index': index,
      'uid': null,
    });
  },
  performAction: function (extraction, action, promise) {
    var self = this;
    promise.done(function (response) {
      toastr.info("Successfully " + action + " extraction");
      extraction.modified = false;
      self.updateExtractions();
    }).fail(function (response) {
      var extraction_error = response.responseJSON.errors || response.responseJSON.detail
      toastr.error("Failed to " + action + " extraction: " + JSON.stringify(extraction_error));
    });
  },
  raiseExtraction: function (extraction) {
    var self = this;
    if (!self.checkSaved()) return;
    self.performAction(
      extraction,
      "update",
      AXW.Requests.PUT(
        "${tg.url(['/dashboard/set_extraction_index', str(dashboard.uid)])}",
        {uid: extraction.uid, index: extraction.index - 1}
      )
    );
  },
  lowerExtraction: function (extraction, status) {
    var self = this;
    if (!self.checkSaved()) return;
    self.performAction(
      extraction,
      "update",
      AXW.Requests.PUT(
        "${tg.url(['/dashboard/set_extraction_index', str(dashboard.uid)])}",
        {uid: extraction.uid, index: extraction.index + 1}
      )
    );
  },
  deleteExtraction: function (extraction) {
    var self = this;
    if (!self.checkSaved() && extraction.modified) self.updateExtractions();
    if (!self.checkSaved()) return;
    if (confirm("Really delete this extraction from dashboard?")) {
      self.performAction(
        extraction,
        "delete",
        AXW.Requests.POST(
          "${tg.url(['/dashboard/delete_extraction', str(dashboard.uid)])}",
	  {uid: extraction.uid}
        )
      );
    }
  },
  saveExtraction: function (extraction) {
    var self = this;
    self.performAction(
      extraction,
      "save",
      AXW.Requests.POST(
        "${tg.url(['/dashboard/save_extraction', str(dashboard.uid)])}",
        extraction
      ).done(function(response){
        toastr.info('Succesfully added widget!');
      }).fail(function(response){
        toastr.error(response.responseText);
      })
    );
  },
  selectExtraction: function (extractionidx, extraction) {
    var self = this;
    $$.get("${tg.url('/dashboard/get_extraction/')}" + extraction.extraction_id, function (res) {
      self.set('extractions.' + extractionidx + '.name', res.extraction.name);
      self.set('extractions.' + extractionidx + '.usual_visualization', res.extraction.visualization);
      self.set('extractions.' + extractionidx + '.graph_axis', res.extraction.graph_axis);
    })
  }
});
