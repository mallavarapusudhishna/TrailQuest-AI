// API Base Configuration (easily updated for local dev or deployment)
const API_BASE_URL = window.location.origin;

document.addEventListener("DOMContentLoaded", () => {
  const questForm = document.getElementById("quest-form");
  const generateBtn = document.getElementById("generate-btn");
  const loadingSpinner = document.getElementById("loading-spinner");
  const errorCard = document.getElementById("error-card");
  const errorMessage = document.getElementById("error-message");
  const questCard = document.getElementById("quest-card");
  const successCard = document.getElementById("success-card");
  const feedbackMessage = document.getElementById("feedback-message");

  const questTitle = document.getElementById("quest-title");
  const questLocationName = document.getElementById("quest-location-name");
  const questAddress = document.getElementById("quest-address");
  const questDifficulty = document.getElementById("quest-difficulty");
  const questDuration = document.getElementById("quest-duration");
  const questDescription = document.getElementById("quest-description");
  const questObjectives = document.getElementById("quest-objectives");
  const questSafety = document.getElementById("quest-safety");

  const statusBtns = document.querySelectorAll(".status-btn");
  const reflectionInput = document.getElementById("reflection");
  const submitCompletionBtn = document.getElementById("submit-completion-btn");
  const newQuestBtn = document.getElementById("new-quest-btn");

  let currentQuestId = null;
  let selectedStatus = null;

  // Form Submission
  questForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const location = document.getElementById("location").value.trim();
    const available_time = parseInt(document.getElementById("available_time").value, 10);
    const activity = document.getElementById("activity").value;
    const difficulty = document.getElementById("difficulty").value;
    const interests = document.getElementById("interests").value.trim();

    if (!location) {
      showError("Please enter a valid location or city.");
      return;
    }

    hide(errorCard);
    hide(questCard);
    hide(successCard);
    show(loadingSpinner);
    generateBtn.disabled = true;

    try {
      const response = await fetch(`${API_BASE_URL}/generate-quest`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          location,
          available_time,
          activity,
          difficulty,
          interests,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to generate quest.");
      }

      displayQuest(data);
    } catch (err) {
      if (err.message.includes("Failed to fetch")) {
        showError("Backend server is unreachable. Please ensure FastAPI is running.");
      } else {
        showError(err.message);
      }
    } finally {
      hide(loadingSpinner);
      generateBtn.disabled = false;
    }
  });

  // Display Quest
  function displayQuest(quest) {
    currentQuestId = quest.quest_id || quest.id;
    selectedStatus = null;

    questTitle.textContent = quest.title;
    questLocationName.textContent = quest.location;
    questAddress.textContent = quest.address ? `📍 ${quest.address}` : "";
    questDifficulty.textContent = quest.difficulty;
    questDuration.textContent = `${quest.estimated_duration} mins`;
    questDescription.textContent = quest.description;
    questSafety.textContent = quest.safety_note;

    questObjectives.innerHTML = "";
    (quest.objectives || []).forEach((obj) => {
      const li = document.createElement("li");
      li.textContent = `☐ ${obj}`;
      questObjectives.appendChild(li);
    });

    // Reset completion controls
    statusBtns.forEach((btn) => btn.classList.remove("selected"));
    reflectionInput.value = "";
    submitCompletionBtn.disabled = true;

    show(questCard);
  }

  // Handle Status Button Clicks
  statusBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      statusBtns.forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedStatus = btn.dataset.status;
      submitCompletionBtn.disabled = false;
    });
  });

  // Submit Completion Result
  submitCompletionBtn.addEventListener("click", async () => {
    if (!currentQuestId || !selectedStatus) return;

    submitCompletionBtn.disabled = true;
    submitCompletionBtn.textContent = "SAVING...";

    try {
      const response = await fetch(`${API_BASE_URL}/quests/${currentQuestId}/complete`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          status: selectedStatus,
          reflection: reflectionInput.value.trim() || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to save completion.");
      }

      // Display status feedback message
      if (selectedStatus === "completed") {
        feedbackMessage.textContent = "Nice work. You touched grass today. 🌿";
      } else if (selectedStatus === "partially_completed") {
        feedbackMessage.textContent = "Still counts. You got outside and made progress. 🌱";
      } else {
        feedbackMessage.textContent = "No worries. The quest will still be here when you're ready. 🌿";
      }

      hide(questCard);
      show(successCard);
    } catch (err) {
      showError(err.message);
    } finally {
      submitCompletionBtn.textContent = "SAVE RESULT";
    }
  });

  newQuestBtn.addEventListener("click", () => {
    hide(successCard);
    document.getElementById("location").focus();
  });

  function show(el) {
    el.classList.remove("hidden");
  }

  function hide(el) {
    el.classList.add("hidden");
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    show(errorCard);
  }
});
