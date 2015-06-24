$(function() {
  $('ul.results li').hover(function(e) {
    if($(this).hasClass('open')) {
      $(this).removeClass('active');
    } else {
      $(this).addClass('active');
    }
  }, function(e) {
    $(this).removeClass('active');
  });
  $('ul.results li .details').click(function(e) {
    $(this).parent().toggleClass('open');
    $(this).parent().removeClass('active');
  });
});
