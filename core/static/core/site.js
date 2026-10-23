(function () {
  var btn = document.querySelector(".menu-btn");
  var nav = document.getElementById("nav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
  // Play the hero mesh animation once, after fonts and layout settle.
  var f = document.querySelector(".fibrin");
  if (f) { requestAnimationFrame(function () { f.classList.add("go"); }); }
})();
