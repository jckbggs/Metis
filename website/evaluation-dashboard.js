let evaluationLogs = [];

function formatBotName(botName) {
  const names = {
    website_information: "Website Information",
    assignment_brief: "Assignment Brief",
    mitigating_circumstances: "Mitigating Circumstances"
  };

  return names[botName] || botName || "Unknown";
}

function formatTime(timestamp) {
  if (!timestamp) return "-";

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;

  return date.toLocaleString();
}

function escapeCsv(value) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}

async function loadEvaluationData() {
  try {
    const response = await fetch("/api/evaluation/logs", {
      credentials: "same-origin"
    });

    const data = await response.json();

    if (data.error) {
      alert(data.error);
      return;
    }

    evaluationLogs = data.logs || [];

    updateSummary(data.summary || {});
    updateTable(evaluationLogs);
  } catch (error) {
    console.error("Failed to load evaluation data:", error);
    alert("Failed to load evaluation data.");
  }
}

function updateSummary(summary) {
  document.getElementById("totalInteractions").textContent =
    summary.total_interactions ?? 0;

  document.getElementById("averageResponse").textContent =
    `${summary.average_response_time_ms ?? 0} ms`;

  document.getElementById("successRate").textContent =
    `${summary.success_rate ?? 0}%`;

  document.getElementById("uniqueParticipants").textContent =
    summary.unique_participants ?? 0;

  document.getElementById("mostUsedBot").textContent =
    summary.most_used_bot ? formatBotName(summary.most_used_bot) : "-";
}

function updateTable(logs) {
  const tbody = document.getElementById("logsTableBody");
  tbody.innerHTML = "";

  if (!logs.length) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="8">No evaluation logs found.</td>';
    tbody.appendChild(row);
    return;
  }

  logs.slice().reverse().forEach(function (item) {
    const row = document.createElement("tr");

    const statusClass = item.success ? "status-success" : "status-fail";
    const statusText = item.success ? "Success" : "Error";

    row.innerHTML = `
      <td>${formatTime(item.timestamp)}</td>
      <td>${item.participant_id || "-"}</td>
      <td>${item.account_type || "-"}</td>
      <td>${formatBotName(item.bot_name)}</td>
      <td class="message-cell"></td>
      <td class="message-cell"></td>
      <td>${item.response_time_ms ?? "-"} ms</td>
      <td class="${statusClass}">${statusText}</td>
    `;

    row.children[4].textContent = item.user_input || "";
    row.children[5].textContent = item.bot_output || "";

    tbody.appendChild(row);
  });
}

function downloadCsv() {
  if (!evaluationLogs.length) {
    alert("No evaluation data to download.");
    return;
  }

  const headers = [
    "timestamp",
    "participant_id",
    "account_type",
    "bot_name",
    "user_input",
    "bot_output",
    "response_time_ms",
    "success",
    "error"
  ];

  const rows = evaluationLogs.map(function (item) {
    return headers.map(function (header) {
      return escapeCsv(item[header]);
    }).join(",");
  });

  const csv = [headers.join(","), ...rows].join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = "metis_evaluation_logs.csv";
  link.click();

  URL.revokeObjectURL(url);
}

document.addEventListener("DOMContentLoaded", loadEvaluationData);