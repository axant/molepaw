var ExtractionVisualization = Ractive.extend({
  template: '#ExtractionVisualization_template',
  data: function () {
    return {
      showAxis: false,
      disabled: true,
      hasError: {
	error: false,
	message: "",
	color: ""
      },
      visualization: {
	type: "${extraction.visualization}",
	original:  "${extraction.visualization}",
        axis: "${extraction.graph_axis}",
        original_axis: "${extraction.graph_axis}"}
    };
  },
  oninit: function () {
    var self=this;
    self.observe('visualization.type', function (newValue, oldValue) {
      if(newValue !== "table"){
        self.set("showAxis", true);
      }else{
        self.set("showAxis", false);
      }

      if(newValue===self.get('visualization.original') && self.get('visualization.axis')===self.get('visualization.original_axis') ){
        self.set('disabled', true);
        self.set('hasError.error', false);
      }
      else {
        self.set('disabled', false);
      }
    });

    self.observe('visualization.axis', function (newValue, oldValue) {
      if(newValue===self.get('visualization.original_axis') && self.get("visualization.type")===self.get("visualization.original")){
        self.set('disabled', true);
        self.set('hasError.error', false);
      }
      else {
        self.set('disabled', false);
      }
    });

  },
  saveVisualization: function () {
    let self=this;
    let re = ".+,.+";
    if(self.get("visualization.type")!== "table" && (self.get("visualization.axis")==="" ||
                                                     self.get("visualization.axis").match(re)===null))
    {
      self.set("hasError.error", true);
      self.set("hasError.message", "Please insert at least two valid columns name (x, y axis).");
      self.set("hasError.color", "red");

    }
    else {
      let data = {visualization: self.get('visualization'), extraction: "${extraction.uid}"};
      $$.ajax({
        url: "${tg.url(['/editor', str(extraction.uid)])}",
        contentType: 'application/json',
        data: JSON.stringify(data),
        type: 'POST',
        success: function (data, textStatus, jqXHR) {
          self.set("visualization.original", self.get("visualization.type"));
          self.set("visualization.original_axis", self.get("visualization.axis"));
          self.set("disabled", true);
          self.set("hasError.error", false);
          self.set("hasError.color", "");
          toastr.success("Successfully updated visualization");
        },
        error: function (xhr, ajaxOptions, thrownError){
          var error_msg = xhr.responseText.match("<strong>(.*)</strong>");
          self.set("hasError.error", true);
          self.set("hasError.message", error_msg[1]);
          self.set("hasError.color", "red");
        }
      });

    }
  }
});
