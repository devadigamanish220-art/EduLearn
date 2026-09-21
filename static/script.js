document.addEventListener("DOMContentLoaded", function () {

    console.log("EduLearn JavaScript Loaded");

    const searchInput =
        document.querySelector("#courseSearch");

    const courseCards =
        document.querySelectorAll(".course-card");

    if (searchInput) {

        searchInput.addEventListener(
            "keyup",
            function () {

                const search =
                    searchInput.value.toLowerCase();

                courseCards.forEach(function (card) {

                    const text =
                        card.innerText.toLowerCase();

                    if (text.includes(search)) {

                        card.style.display = "block";

                    } else {

                        card.style.display = "none";

                    }

                });

            }
        );

    }

});