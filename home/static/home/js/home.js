// ----------- HOMEPAGE JS ------------- //


// HTML Content for blurbs
var aboutText = "I just wanna help out!";
var linksText = "Add something here later about links";
var contactText = "Contact stuff";
var legalText = "The information contained on HTMLPrep.com and any publications or study materials created by the author of HTMLPrep.com is for informational purposes only. They are to be used to study and review for the ACT, SAT, or GRE. Exam content review, methods of study, tips and sample questions are only recommendations from the author, and reading any information on HTMLPrep.com and any publications or other study materials created by the author does not guarantee passing any of the aforementioned exams. The author has made reasonable efforts to provide current and accurate information. The author will not be held liable for any unintentional errors or omissions that may be found.";


// Open Homepage
$("#start").on('click', function(event) {
    event.preventDefault();
    $("#jumbo1").fadeOut(400, function() {
        $("#jumbo1").remove();
        $("#page2").fadeTo(400, 1);
    });
});


// Fade out blurb, change html, change active state, fade in
$(".pill").on('click', function(event) {
    event.preventDefault();

    // deactivate all pills
    deactivateAll();

    // activate selected pill
    $(this).addClass("active");

    // fade out title and text, change each mid fade
    var id = checkId($(this).attr("id"));
    $("#title").fadeOut(150, function() {
        $("#title").text(id[0]);
    });
    $("#text").fadeOut(150, function() {
        $("#text").text(id[1]);
    });
    // fade back in

    $("#title").fadeIn();
    $("#text").fadeIn();
});


// Shut off all menu pills before reactivating selected one
function deactivateAll() {
    $.each($(".pill"), function() {
        $(this).removeClass("active");
    });
}


// Return id of selected pill
function checkId(id) {
    if(id === "about") {
        return ["About Us", aboutText];
    }
    else if(id === "links") {
        return ["Links", linksText];
    }
    else if(id === "contact") {
        return ["Contact", contactText];
    }
    else if(id === "legal") {
        return ["Legal", legalText];
    }
}
