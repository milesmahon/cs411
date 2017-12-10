    $.ajax({
        type: 'GET',
        cache: false,
        url: "{{ url_for('get_data', sessionname=sessionnamme) }}"
        success: function(resp){
            $("#in_session").html(resp.in_session);
    }
    });