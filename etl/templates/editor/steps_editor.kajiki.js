var StepsEditor = Ractive.extend({
  template: '#StepsEditor_template',
  data: function () { return {
    docstring: JSON.parse('${docstring}'),
  }},
  oninit: function () {
    var self = this;
    self.set('testrun', []);
    self.updateSteps();
    self.observe('steps.*.function', function (newValue, oldValue, keypath) {
      var stepkeypath = keypath.substring(0, keypath.lastIndexOf('.'));
      var stepidx = stepkeypath.substring(stepkeypath.lastIndexOf('.') + 1)
      if (newValue !== 'select_function') {
        if (self.get('loaded') === true) {
	  self.set(stepkeypath + '.modified', true);
        }
      }
      self.set(stepkeypath + '.function_doc', self.get('docstring')[self.get('steps')[stepidx].function]);
    });
    self.observe('steps.*.options', function (newValue, oldValue, keypath) {
      if (self.get('loaded') === true) {
        var stepkeypath = keypath.substring(0, keypath.lastIndexOf('.'));
        self.set(stepkeypath + '.modified', true);
      }
    });

  },
  updateSteps: function () {
    var self = this;
    self.set('loaded', false);
    $$.get("${tg.url(['/editor', str(extraction.uid), 'steps'])}", function (res) {
      self.set('steps', res.steps);
      self.set('loaded', true);
      self.set('steps_legth_at_last_update', self.get('steps').length);
    });
    $$.get("${tg.url(['/editor', str(extraction.uid), 'test_pipeline'])}", function (res) {
      self.set('testrun', res.results);
    });
  },
  checkSaved: function () {
    var self = this;
    return self.get('steps_legth_at_last_update') == self.get('steps').length;
  },
  addStep: function () {
    var self = this;
    var priority = 0;
    if (self.get('steps').length)
      priority = self.get('steps')[self.get('steps').length - 1].priority + 1;
    self.push('steps', {
      'function': 'select_function',
      'function_doc': "${_('select the function for this step by clicking the title of the step')}",
      'priority': priority,
      'enabled': true
    });
  },
  performAction: function (step, action, promise) {
    var self = this;
    promise.done(function (response) {
      toastr.info("Successfully " + action + " step");
      step.modified = false;
      self.updateSteps();
    }).fail(function (response) {
      var step_error = response.responseJSON.errors || response.responseJSON.detail;
      toastr.error("Failed to " + action + " step: " + JSON.stringify(step_error));
    });
    self.observe('self',function (newValue, oldValue, keypath) {
      extractionvisualization.saveVisualization();
    });
  },
  showSave: function(event, stepidx) {
    event.original.preventDefault();
    var self = this;
  },
  toggleStep: function (step, status) {
    var self = this;
    if (!self.checkSaved()) return;
    self.performAction(
      step,
      "update",
      AXW.Requests.POST(
        "${tg.url(['/editor', str(extraction.uid), 'steps', 'toggle'])}",
        $$.extend({}, step, {'enabled': status})
      )
    );


  },
  raiseStep: function (step, status) {
    var self = this;
    if (!self.checkSaved()) return;
    self.performAction(
      step,
      "update",
      AXW.Requests.PUT(
        "${tg.url(['/editor', str(extraction.uid), 'steps'])}",
        {uid: step.uid, priority: step.priority - 1}
      )
    );
  },
  lowerStep: function (step, status) {
    var self = this;
    if (!self.checkSaved()) return;
    self.performAction(
      step,
      "update",
      AXW.Requests.PUT(
        "${tg.url(['/editor', str(extraction.uid), 'steps'])}",
        {uid: step.uid, priority: step.priority + 1}
      )
    );
  },
  deleteStep: function (step) {
    var self = this;
    if (step.function === 'select_function') self.updateSteps();
    if (!self.checkSaved() && step.modified) self.updateSteps();
    if (!self.checkSaved()) return;
    if (confirm("Really delete this step?")) {
      self.performAction(
        step,
        "delete",
        AXW.Requests.DELETE(
          "${tg.url(['/editor', str(extraction.uid), 'steps'])}/" + step.uid
        )
      );
    }
  },
  saveStep: function (step) {
    var self = this;
    if (step.uid !== undefined) {
      self.performAction(
        step,
        "update",
        AXW.Requests.PUT(
          "${tg.url(['/editor', str(extraction.uid), 'steps'])}",
          step
        )
      );
    }
    else {
      self.performAction(
        step,
        "create",
        AXW.Requests.POST(
          "${tg.url(['/editor', str(extraction.uid), 'steps'])}",
          step
        )
      );
    }
  }
});
