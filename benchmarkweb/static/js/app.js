$(function() {
  $.cookie('juju.secret', 'f9dc7be6d403b3e0f157f9f0c2538348')
  $.cookie('juju.user', 'user-admin')
  s = $.cookie('juju.secret');
  u = $.cookie('juju.user');
  $.post('/api', {'juju.api.secret': s, 'juju.api.user': u}, function(data) {
    console.log(data);
    for(var t in data.benchmarks) {
      $.each(data.benchmarks[t]['actions'], function(i, benchs) {
        console.log(i, benchs);
        create_row(t, benchs);
      });
    }
  });
});

var build_params = function(params) {
  p = '';
  for(k in params) {
    p = p + ' ' + k + '=' + params[k];
  }
  return p
}

var create_row = function(name, d) {
  r = $('li.template').clone();
  r.removeClass('template');
  r.find('div.name').text(name);
  r.find('div.status').text(d.status);
  r.find('pre.command').text('juju action do ' + d.unit + ' ' + d.action.name + build_params(d.action.parameters));
  if('output' in d) {
    if('meta' in d.output) {
      r.find('div.time').text(d.output.meta.start);
      if('composite' in d.output.meta) {
        r.find('div.score').text(d.output.meta.composite.value + ' ' + d.output.meta.composite.units);
      }
    } else {
      r.find('div.time').text(d.started);
    }

    r.find('pre.result').text(YAML.stringify(d.output, 4, 2));
  } else {
    r.find('div.time').text(d.started);
  }
  r.bind({
    mouseenter: result_hover_in,
    mouseleave: result_hover_out
  });
  r.find('div.row.details').bind({
    click: result_click
  });
  r.appendTo('ul.results');
};

var result_hover_in = function(e) {
  if($(this).hasClass('open')) {
    $(this).removeClass('active');
  } else {
    $(this).addClass('active');
  }
};

var result_hover_out = function(e) {
    $(this).removeClass('active');
};

var result_click = function(e) {
  $(this).parent().toggleClass('open');
  $(this).parent().removeClass('active');
};
