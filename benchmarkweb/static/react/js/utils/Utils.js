var React = require('react');
var moment = require('moment');

var status_color_map = {
  'completed': 'green',
  'cancelled': 'red',
  'failed': 'red',
  'pending': 'yellow',
  'running': 'blue',
  'canceling': 'yellow'
}

var Utils = {

  statusColor: function(status) {
    return status_color_map[status];
  },

  formatResult: function(val) {
    if (val && val.value) {
      return val.value + ' ' + (val.units || '');
    }
    return val;
  },

  timeDeltaHtml: function(strDate) {
    if (!strDate) {
      return null;
    }

    var started = moment(strDate);
    var displayDate;

    if (moment().diff(started, 'days') > 30) {
      displayDate = started.format('YYYY-MM-DD');
    }
    else {
      displayDate = started.fromNow();
    }

    return (
      <span title={strDate.replace("T", " ")}>
        {displayDate}
      </span>
    );
  }

}

module.exports = Utils;
