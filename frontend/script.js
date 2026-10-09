const API_BASE_URL = window.location.origin;

const FEEDBACK = {
  completed: "Quest complete. Nice work getting outside.",
  partially_completed: "Progress counts. Thanks for giving it a try.",
  not_completed: "No worries. You can try again when it works for you.",
};

document.addEventListener("DOMContentLoaded", () => {
  loadStorageNotice();

  const questForm = document.getElementById("quest-form");
  const generateBtn = document.getElementById("generate-btn");
  const loadingSpinner = document.getElementById("loading-spinner");
  const errorCard = document.getElementById("error-card");
  const errorMessage = document.getElementById("error-message");
  const questCard = document.getElementById("quest-card");
  const successCard = document.getElementById("success-card");
  const feedbackTitle = document.getElementById("feedback-title");
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

  questForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const location = document.getElementById("location").value.trim();
    const available_time = parseInt(document.getElementById("available_time").value, 10);
    const activity = document.getElementById("activity").value;
    const difficulty = document.getElementById("difficulty").value;
    const interests = document.getElementById("interests").value.trim();

    if (location.length < 2) {
      showError("Please enter a valid location (at least 2 characters).");
      return;
    }

    if (available_time < 15 || available_time > 180) {
      showError("Available time must be between 15 and 180 minutes.");
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          location,
          available_time,
          activity,
          difficulty,
          interests,
        }),
      });

      let data = {};
      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (!response.ok) {
        const detail = data.detail;
        const msg = Array.isArray(detail)
          ? detail.map((d) => d.msg).join(" ")
          : detail || "Failed to generate quest.";
        throw new Error(msg);
      }

      displayQuest(data);
    } catch (err) {
      if (err.message.includes("Failed to fetch")) {
        showError("Cannot reach the server. Start FastAPI with uvicorn and open this page from http://127.0.0.1:8000");
      } else {
        showError(err.message);
      }
    } finally {
      hide(loadingSpinner);
      generateBtn.disabled = false;
    }
  });

  function displayQuest(quest) {
    currentQuestId = quest.quest_id || quest.id;
    selectedStatus = null;

    questTitle.textContent = quest.title;
    questLocationName.textContent = quest.location;
    questAddress.textContent = quest.address || "";
    questDifficulty.textContent = quest.difficulty;
    questDuration.textContent = `${quest.estimated_duration} min`;
    questDescription.textContent = quest.description;
    questSafety.textContent = quest.safety_note;

    questObjectives.innerHTML = "";
    (quest.objectives || []).forEach((obj) => {
      const li = document.createElement("li");
      li.textContent = obj;
      questObjectives.appendChild(li);
    });

    statusBtns.forEach((btn) => btn.classList.remove("selected"));
    reflectionInput.value = "";
    submitCompletionBtn.disabled = true;

    hide(errorCard);
    show(questCard);
    questCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  statusBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      statusBtns.forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedStatus = btn.dataset.status;
      submitCompletionBtn.disabled = false;
    });
  });

  submitCompletionBtn.addEventListener("click", async () => {
    if (!currentQuestId || !selectedStatus) return;

    const priorQuestVisible = !questCard.classList.contains("hidden");
    submitCompletionBtn.disabled = true;
    const originalLabel = submitCompletionBtn.textContent;
    submitCompletionBtn.textContent = "Saving…";

    try {
      const response = await fetch(`${API_BASE_URL}/quests/${currentQuestId}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: selectedStatus,
          reflection: reflectionInput.value.trim() || null,
        }),
      });

      let data = {};
      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (!response.ok) {
        throw new Error(data.detail || "Failed to save completion.");
      }

      feedbackTitle.textContent = "Saved";
      feedbackMessage.textContent = FEEDBACK[selectedStatus] || "Thank you for logging your quest.";
      hide(questCard);
      show(successCard);
      successCard.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      if (priorQuestVisible) {
        show(questCard);
      }
      showError(err.message);
    } finally {
      submitCompletionBtn.textContent = originalLabel;
      submitCompletionBtn.disabled = !selectedStatus;
    }
  });

  newQuestBtn.addEventListener("click", () => {
    hide(successCard);
    document.getElementById("form-card").scrollIntoView({ behavior: "smooth" });
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
    errorCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  async function loadStorageNotice() {
    const el = document.getElementById("storage-notice");
    if (!el) return;
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) return;
      const data = await response.json();
      const storage = data.storage;
      if (!storage) return;
      el.textContent = storage.message || "";
      el.classList.remove("hidden");
      if (storage.durable) {
        el.classList.add("storage-ok");
      }
    } catch {
      /* ignore — server may be offline until user starts it */
    }
  }
});
