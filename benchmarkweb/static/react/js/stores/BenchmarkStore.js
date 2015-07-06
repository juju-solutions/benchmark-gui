var AppDispatcher = require('../dispatcher/AppDispatcher');
var EventEmitter = require('events').EventEmitter;
var BenchmarkConstants = require('../constants/BenchmarkConstants');
var assign = require('object-assign');

var CHANGE_EVENT = 'change';

var _data = {};
var _index = {};


/**
 * Refetch all benchmark data.
 */
function fetchAll() {
  var url = '/api';
  $.ajax({
    url: url,
    dataType: 'json',
    success: function(data) {
      _data = data;
      refreshIndex();
      BenchmarkStore.emitChange();
    },
    error: function(xhr, status, err) {
      console.error(url, status, err.toString());
    }
  });
}

/**
 * Create an index into _data, by action uuid.
 */
function refreshIndex() {
  var benchmarks = _data.benchmarks;
  var benchmark, action;

  if (!benchmarks) {
    return;
  }

  _index = {};

  for (var b in benchmarks) {
    benchmark = benchmarks[b];
    if (!benchmark.actions) {
      continue;
    }
    for (var i in benchmark.actions) {
      action = benchmark.actions[i];
      _index[action.uuid] = action;
    }
  }
}


var BenchmarkStore = assign({}, EventEmitter.prototype, {

  /**
   * Get one benchmark by uuid.
   * @param {string} uuid
   * @return {object}
   */
  get: function(uuid) {
    return _index[uuid];
  },

  /**
   * Get the entire collection of BENCHMARKs.
   * @return {object}
   */
  getAll: function() {
    return _data;
  },

  getIndex: function() {
    return _index;
  },

  getSettings: function() {
    return _data.settings;
  },

  getEnvironment: function() {
    return _data.environment;
  },

  getEnvironmentCount: function() {
    return _data.environment_count;
  },

  emitChange: function() {
    this.emit(CHANGE_EVENT);
  },

  /**
   * @param {function} callback
   */
  addChangeListener: function(callback) {
    this.on(CHANGE_EVENT, callback);
  },

  /**
   * @param {function} callback
   */
  removeChangeListener: function(callback) {
    this.removeListener(CHANGE_EVENT, callback);
  }
});

// Register callback to handle all updates
AppDispatcher.register(function(action) {

  switch(action.actionType) {

    case BenchmarkConstants.BENCHMARK_REFRESH_ALL:
      fetchAll();
      break;

    default:
      // no op
  }
});

module.exports = BenchmarkStore;
