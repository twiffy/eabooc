$( document ).ready( function() {

  $( '.collapsible' ).before( '<a class="collapser">click to show instructions</a>' );
  $( '.collapsible' ).css('display', 'none');
  $( 'a.collapser' ).click(function() {
    $(this).next().toggle(200)
    return false;
  });

});
