/*======================
========================*/

(function ($) {
  "use strict";

  /*========== Preloader ==========*/
  $(window).on("load", () => {
    $("#preloader").fadeOut(500);
  });

  $(document).ready(function ($) {
    /*========= sticky menu ==========*/
    $(window).scroll(function () {
      try {
        var window_top = $(window).scrollTop() + 1;
        var header = $(".header");
        if (window_top > 200) {
          header.addClass("header_fixed animate__animated animate__fadeIn");
        } else {
          header.removeClass("header_fixed animate__animated animate__fadeIn");
        }
      } catch (error) {
        console.error("An error occurred while handling scroll:", error);
      }
    });

    /*========= Modal Video ==========*/
    try {
      $(".video-btn").modalVideo({
        channel: "youtube",
      });
    } catch (error) {
      console.log("Modal Video Not Loded");
    }
    try {
      $(".play-btn").modalVideo({
        channel: "youtube",
      });
    } catch (error) {
      console.log("Modal Video Not Loded");
    }

    /*========= Nice Select js ==========*/
    try {
      $("select").niceSelect();
    } catch (error) {
      console.log("Nice select not enable this page");
    }


    /*============ offcanvase Menu =========*/
    try {
      $(".offcanvase__menu--close-icon, .offcanvas__overlay").on(
        "click",
        function () {
          $(".offcanvase").removeClass("info-open");
          $(".offcanvas__overlay").removeClass("overlay-open");
        }
      );
      $(".menu-icon").on("click", function () {
        $(".offcanvase").addClass("info-open");
        $(".offcanvas__overlay").addClass("overlay-open");
      });
    } catch (error) {
      console.log("offcanvase Menu Not loaded");
    }

    /*========= Mobile Menu =========*/
    try {
      $("#offcanvase__menu").meanmenu({
        meanMenuContainer: ".offcanvase-menu",
        meanScreenWidth: "767",
        meanExpand: ["+"],
      });
    } catch (error) {
      console.log("Mobile Menu Not loaded");
    }

    // accordion click
    const buttons = document.querySelectorAll(".accordion-button");
    const items = document.querySelectorAll(".accordion-item");
    buttons.forEach((button, index) => {
      button.addEventListener("click", () => {
        items.forEach((item) => item.classList.remove("active"));
        items[index].classList.add("active");
      });
    });

    // video embaded
    $(function () {
      var videoBtn = $(".playing-btn");
      videoBtn.click(function () {
        var videoContainer = $(this).closest(".video-container");
        var src = videoContainer.data("url");
        var title = videoContainer.data("title");
        var videoFrame = $("<iframe>", {
          src: src,
          frameborder: 0,
          title: title,
          allow:
            "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
          class: "video-iframe",
        });

        videoContainer.append(videoFrame);
      });
    });

    /*============= Sponsor Slider =============*/
    $(".sponsor__slider").slick({
      autoplay: true,
      arrows: false,
      centerMode: true,
      pauseOnHover: true,
      slidesToShow: 5,
      slidesToScroll: 5,
      responsive: [
        {
          breakpoint: 1024,
          settings: {
            slidesToShow: 4,
            slidesToScroll: 4,
            infinite: true,
          },
        },
        {
          breakpoint: 600,
          settings: {
            slidesToShow: 3,
            slidesToScroll: 3,
            centerMode: false,
          },
        },
        {
          breakpoint: 480,
          settings: {
            slidesToShow: 2,
            slidesToScroll: 2,
            centerMode: false,
          },
        },
      ],
    });

    /*============= testimonial Slider-2 =============*/

    $(".testimonial__slider-two").slick({
      autoplay: true,
      arrows: false,
      pauseOnHover: true,
      slidesToShow: 3,
      slidesToScroll: 3,
      centerMode: true,
      dots: true,
      responsive: [
        {
          breakpoint: 1300,
          settings: {
            slidesToShow: 3,
            centerMode: true,
            slidesToScroll: 3,
            infinite: true,
          },
        },
        {
          breakpoint: 1200,
          settings: {
            slidesToShow: 3,
            slidesToScroll: 3,
            infinite: true,
          },
        },
        {
          breakpoint: 991,
          settings: {
            slidesToShow: 2,
            slidesToScroll: 2,
            centerMode: false,
          },
        },
        {
          breakpoint: 575,
          settings: {
            slidesToShow: 1,
            slidesToScroll: 1,
            centerMode: false,
          },
        },
      ],
    });

    /*============= testimonial Slider =============*/
    $(".testimonial__wrapper").slick({
      autoplay: true,
      arrows: false,
      pauseOnHover: true,
      slidesToShow: 4,
      slidesToScroll: 4,
      cssEase: "ease",
      dots: true,
      centerMode: true,
      responsive: [
        {
          breakpoint: 1300,
          settings: {
            slidesToShow: 3,
            centerMode: true,
            slidesToScroll: 3,
            infinite: true,
          },
        },
        {
          breakpoint: 1200,
          settings: {
            slidesToShow: 3,
            slidesToScroll: 3,
            infinite: true,
          },
        },
        {
          breakpoint: 991,
          settings: {
            slidesToShow: 2,
            slidesToScroll: 2,
            centerMode: false,
          },
        },
        {
          breakpoint: 575,
          settings: {
            slidesToShow: 1,
            slidesToScroll: 1,
            centerMode: false,
          },
        },
      ],
    });

    /*============= stylish Slider =============*/

    $(".stylish__slide").slick({
      autoplay: true,
      arrows: false,
      pauseOnHover: true,
      centerMode: true,
      slidesToShow: 3,
      slidesToScroll: 3,
      cssEase: "ease-in",
      infinite: true,
      dots: true,
      responsive: [
        {
          breakpoint: 1300,
          settings: {
            slidesToShow: 3,
            slidesToScroll: 3,
            centerMode: true,
          },
        },
        {
          breakpoint: 991,
          settings: {
            slidesToShow: 2,
            slidesToScroll: 2,
            centerMode: true,
          },
        },
        {
          breakpoint: 575,
          settings: {
            slidesToShow: 1,
            slidesToScroll: 1,
            centerMode: false,
          },
        },
      ],
    });

    /*======= Popular Post Slider =========*/

    $(".case-slider").slick({
      autoplay: true,
      dots: false,
      pauseOnHover: false,
      slidesToShow: 1,
      slidesToScroll: 1,
      arrows: true,
      prevArrow: '.left_arrow',
      nextArrow: '.right_arrow',
      responsive: [
        {
          breakpoint: 575,
          settings: {
            slidesToShow: 1,
            slidesToScroll: 1,
            arrows: false,
          },
        },
      ],
    });

    /*========= progress bar =======*/
    try {
      const progressBars = document.querySelectorAll(".progress-bar");
      progressBars.forEach((progressBar) => {
        const ariaValuenow = progressBar.getAttribute("aria-valuenow");
        progressBar.style.width = `${ariaValuenow}%`;
      });
    } catch (error) {
      console.log("progress bar not enable this page");
    }
  });

  // change image

  /*=========== Tab Js ===========*/
  try {
    $(".tab__button").click(function () {
      const tabId = $(this).data("tab");
      $(".tab__button").removeClass("active");
      $(this).addClass("active");
      $(".tab__content").removeClass("open").hide();
      $("#" + tabId)
        .addClass("open")
        .show();
    });
    $('.tab__button[data-tab="tab1"]').click();
  } catch (error) {
    console.error("Tab Button not enable this page", error);
  }

  /*======== Price Range =========*/
  try {
    function updateValues() {
      var rangeValue = $("#priceRange").val();
      $(".value-left").text("0");
      $(".value-right").text("$" + rangeValue);
    }
    $("#priceRange").on("input", function () {
      updateValues();
    });
    updateValues();
  } catch (error) {
    console.log("Range Only Enable for Product page");
  }

  /*======== Delete Cart item =========*/
  try {
    function handleDeleteClick(event) {
      const row = event.target.closest("tr");
      if (row) {
        row.remove();
      }
    }
    const deleteIcons = document.querySelectorAll(".cart__delete");
    deleteIcons.forEach((icon) => {
      icon.addEventListener("click", handleDeleteClick);
    });
  } catch (error) {
    console.log("Table Delete only enable for cart Page");
  }

  /*========== Button scroll up js ===========*/
  var scrollPath = document.querySelector(".scroll path");
  var pathLength = scrollPath.getTotalLength();
  scrollPath.style.transition = scrollPath.style.WebkitTransition = "none";
  scrollPath.style.strokeDasharray = pathLength + " " + pathLength;
  scrollPath.style.strokeDashoffset = pathLength;
  scrollPath.getBoundingClientRect();
  scrollPath.style.transition = scrollPath.style.WebkitTransition =
    "stroke-dashoffset 10ms linear";
  var updatescroll = function () {
    var scroll = $(window).scrollTop();
    var height = $(document).height() - $(window).height();
    var scroll = pathLength - (scroll * pathLength) / height;
    scrollPath.style.strokeDashoffset = scroll;
  };
  updatescroll();
  $(window).scroll(updatescroll);
  var offset = 50;
  var duration = 950;
  jQuery(window).on("scroll", function () {
    if (jQuery(this).scrollTop() > offset) {
      jQuery(".scroll").addClass("active-scroll");
    } else {
      jQuery(".scroll").removeClass("active-scroll");
    }
  });
  jQuery(".scroll").on("click", function (event) {
    event.preventDefault();
    jQuery("html, body").animate(
      {
        scrollTop: 0,
      },
      duration
    );
    return false;
  });
})(jQuery);
