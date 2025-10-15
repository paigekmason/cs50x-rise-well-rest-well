// All HTML content loads prior to JavaScript code running
document.addEventListener("DOMContentLoaded", async () => {

    // Checks that username exists, stops code from running if it doesn't
    if (typeof username === "undefined" || !username) {
        console.error("Username not found — make sure it's passed from Flask with tojson.");
        return;
    }

    // Stores date for today only (YYYY-MM-DD format)
    const today = new Date().toISOString().slice(0, 10);

    // Creates unique keys for each user's daily affirmation
    const affKey = `${username}_affirmationData`;
    const savedAff = JSON.parse(localStorage.getItem(affKey)) || {};

    // If user already got an affirmation today, fetches it from localStorage
    // Else, fetches new affirmation from the API
    let affirmationText;

    if (savedAff.date === today && savedAff.text) {
        affirmationText = savedAff.text;
    } else {
        const response = await fetch('https://corsproxy.io/?https://www.affirmations.dev/');
        const data = await response.json();
        affirmationText = data.affirmation;

        localStorage.setItem(affKey, JSON.stringify({
            text: affirmationText,
            date: today
        }));
    }

    // Inserts the text using id "affirmation" with fade-in effect
    const affElem = document.getElementById("affirmation");
    if (affElem) {
        affElem.textContent = affirmationText;
        affElem.classList.add("fade-in");
    }

    // Retrieves daily form and completed message from the HTML
    const dailyForm = document.getElementById("daily_form");
    const completedMessage = document.getElementById("completed_message");

    // User-specific key to store the date this user last completed it
    const formKey = `${username}_formCompletedDate`;

    const lastCompleted = localStorage.getItem(formKey);

    // Hides the form if user has already completed it today
    if (dailyForm && completedMessage) {
        if (lastCompleted === today) {
            dailyForm.style.display = "none";
            completedMessage.style.display = "block";
        }

        // If user submits form, collect form fields to be sent back to Flask
        dailyForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            // Collect all form fields
            const formData = new FormData(dailyForm);

            // Send to the Flask route defined in the form’s action attribute
            try {
                const response = await fetch(dailyForm.action, {
                    method: "POST",
                    body: formData,
                });

                // Flask received it and processed successfully, hide form and show message
                // Else, displays error message
                if (response.ok) {
                    localStorage.setItem(formKey, today);
                    dailyForm.style.display = "none";
                    completedMessage.style.display = "block";
                } else {
                    console.error("Server error:", response.statusText);
                    alert("Something went wrong while submitting your form. Try again!");
                }
            } catch (err) {
                console.error("Network error:", err);
                alert("Network error — please check your connection.");
            }
        });
    }

    // Finds all check buttons in the HTML code
    const checkButtons = document.querySelectorAll('.check-btn');
    const stepsKey = `${username}_completedSteps`;

    // If no saved completed steps, initialize an empty list
    let savedSteps = JSON.parse(localStorage.getItem(stepsKey)) || {
        date: today,
        completed: []
    };

    // Reset completed steps if new day
    if (savedSteps.date !== today) {
        savedSteps = {
            date: today,
            completed: []
        };
        localStorage.setItem(stepsKey, JSON.stringify(savedSteps));
    }

    // Find the row and the text for each step
    checkButtons.forEach(button => {
        const row = button.closest('tr');
        const stepText = row.querySelector('.step-text');

        // Cross out completed steps if page reloads
        if (savedSteps.completed.includes(stepText.textContent)) {
            stepText.classList.add('step-completed', 'fade-in');
        }

        // Cross out step when check button is clicked, unless already completed, then un-cross the step
        button.addEventListener('click', () => {
            stepText.classList.toggle('step-completed');
            stepText.classList.add('fade-in');

            if (stepText.classList.contains('step-completed')) {
                if (!savedSteps.completed.includes(stepText.textContent)) {
                    savedSteps.completed.push(stepText.textContent);
                }
            } else {
                savedSteps.completed = savedSteps.completed.filter(s => s !== stepText.textContent);
            }

            localStorage.setItem(stepsKey, JSON.stringify(savedSteps));
        });

        // Store the user's scroll position, to be remembered when refreshed
        window.addEventListener("beforeunload", () => {
            sessionStorage.setItem("scrollPosition", window.scrollY);
        });

        // Automatically direct the page to user's saved scroll position
        window.addEventListener("load", () => {
            const scrollPosition = sessionStorage.getItem("scrollPosition");
            if (scrollPosition) {
                window.scrollTo(0, parseInt(scrollPosition));
            }
        });
    });
});
