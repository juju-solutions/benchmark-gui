var AppDispatcher = require('../dispatcher/AppDispatcher');
var BenchmarkConstants = require('../constants/BenchmarkConstants');

var BenchmarkActions = {

  refreshAll: function() {
    AppDispatcher.dispatch({
      actionType: BenchmarkConstants.BENCHMARK_REFRESH_ALL
    });
  }

};

module.exports = BenchmarkActions;
