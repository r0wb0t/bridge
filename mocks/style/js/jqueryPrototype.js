// Lets you add an attribute to links that maintains the scroll positions
// e.g. <a href="B.html" data-keepscroll="yes">Go</a>

$(document).ready(function() {

  var match = location.href.match(/\bscroll=(\d+)/);
  if (match) {
    var scrollTop = parseInt(match[1]);

    $(window).scrollTop(scrollTop);
  }

  History.Adapter.bind(window,'statechange', function() { 
    var data = History.getState().data;
    var screen;
    if (data.show) {
      screen = data.show;
    } else {
      screen = 'screen01';
    }
    var scrollTop = $(window).scrollTop();

    $(".screen").css({display: 'none'});
    $('#' + screen).css({display: 'block'});

    $(window).scrollTop(scrollTop);
  });

  $('a').click(function(e) {
    var link = $(this);
    if (link.data('keepscroll')) {
      // Get scroll value.
      var scrollTop = $(window).scrollTop();

      // Cancel the click so we can change the link.
      e.preventDefault();

      // Open link at scroll value.
      location.href = link.get(0).href + '?scroll=' + scrollTop;
    } else if (link.data('replace')) {
      e.preventDefault();

      History.pushState({'show': link.data('replace')}, null, '?screen=' + link.data('replace'));
    }
  });

});
