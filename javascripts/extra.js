/* Connect to Etsy API — disclaimer gate
   Hides the setup guide content until the user clicks the accept button.
   On accept: hides the disclaimer, reveals the guide content. */
document.addEventListener("DOMContentLoaded", function () {
	var disclaimer = document.getElementById("api-disclaimer");
	var guide = document.getElementById("api-guide");
	var btn = document.getElementById("api-disclaimer-accept");

	if (!disclaimer || !guide || !btn) return;

	guide.style.display = "none";

	btn.addEventListener("click", function () {
		disclaimer.style.display = "none";
		guide.style.display = "block";
	});
});
