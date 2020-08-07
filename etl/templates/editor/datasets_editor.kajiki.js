var DataSetsEditor = Ractive.extend({
  template: '#DataSetsEditor_template',
  data: function() { return {
    datasets_columns: ${h.script_json_encode(datasets_columns)},
    available_datasets: ${h.script_json_encode(available_datasets)},
    getCols: function () {
      var datasets_count = 0;
      var datasets = this.get('datasets');
      if (datasets)
        datasets_count = datasets.length;
      return Math.max(3, Math.round(12 / (datasets_count + 1)));
    },
    hasAtLeastOneDataset: function () {
      var datasets = this.get('datasets');
      if (datasets)
        return datasets.length >= 1;
      return false;
    },
    notEditingFirstDataset: function () {
      var datasets = this.get('datasets');
      var editingdataset = this.get('editingdataset');
      return datasets[0].uid !== editingdataset.uid
    }
  }},
  oninit: function () {
    var self = this;
    self.updateDataSets();
  },
  updateDataSets: function () {
    var self = this;
    $$.get("${tg.url(['/editor', str(extraction.uid), 'datasets'])}", function (res) {
      self.set('datasets', res.datasets);
      self.set('sampledata', res.sampledata);
    });
  },
  addDataSet: function () {
    var self = this;
    AXW.Requests.POST(
      "${tg.url(['/editor', str(extraction.uid), 'datasets'])}",
      self.get('newdataset')
    ).done(function (response) {
      console.log(self, response)
      toastr.info("Successfully added dataset");
      self.set('addingdataset', false);
      self.set('newdataset', {});
      self.updateDataSets();
    }).fail(function (response) {
      toastr.error("Failed to add dataset: " + JSON.stringify(response.responseJSON.errors));
    });
  },
  dismissEdit: function() {
    this.set({'editingdataset': false, 'addingdataset': false});
    this.updateDataSets();
  },
  editDataset: function(dataset) {
    var self = this;
    self.set({'editingdataset': dataset, 'addingdataset': false})
    var dataset = document.getElementById('editingdatset-dataset-selected');
    if (dataset) dataset.selected = 'selected';
    var join_self_col = document.getElementById('editingdataset-join_self_col-selected');
    if (join_self_col) join_self_col.selected = 'selected';
    var join_type = document.getElementById('editingdataset-join_type-selected');
    if (join_type) join_type.selected = 'selected';
    var join_other_col = document.getElementById('editingdataset-join_other_col-selected')
    if (join_other_col) join_other_col.selected = 'selected';
  },
  modifyDataset: function () {
    var self = this;
    AXW.Requests.PUT(
      "${tg.url(['/editor', str(extraction.uid), 'datasets'])}",
      self.get('editingdataset'),
    ).done(function (response) {
      toastr.info('dataset updated');
      self.set('editingdataset', false);
      self.updateDataSets();
    }).fail(function (response) {
      toastr.error("failed to modify dataset: " + JSON.stringify(response.responseJSON.errors));
    })
  },
  deleteDataset: function (dataset) {
    var self = this;
    if (confirm("Really delete this dataset?")) {
      $$.ajax({
        url: "${tg.url(['/editor', str(extraction.uid), 'datasets'])}" + '/' + dataset.uid,
        type: 'DELETE',
      }).done(function (response) {
        toastr.info('dataset deleted');
        self.updateDataSets();
      }).fail(function (response) {
        toastr.error("failed to delete dataset: " + JSON.stringify(response.responseJSON.errors));
      })
    }
  }
});
