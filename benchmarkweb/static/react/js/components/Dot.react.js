var React = require('react');

var Dot = React.createClass({
  render: function() {
    return (
      <span {...this.props}>&#9679;</span>
    );
  }
});

module.exports = Dot;
