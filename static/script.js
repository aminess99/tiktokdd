document.getElementById('search-btn').addEventListener('click', () => {
    const videoUrl = document.getElementById('video-url').value;
    const optionsDiv = document.getElementById('options');
    const resultDiv = document.getElementById('result');

    if (!videoUrl) {
        resultDiv.innerHTML = '<p class="text-danger">Please enter a TikTok video URL.</p>';
        return;
    }

    optionsDiv.classList.remove('d-none');
    resultDiv.innerHTML = '<p class="text-success">URL is valid. Choose an option below.</p>';
});

document.getElementById('download-video').addEventListener('click', async () => {
    await downloadFile('video');
});

document.getElementById('download-audio').addEventListener('click', async () => {
    await downloadFile('audio');
});

async function downloadFile(type) {
    const videoUrl = document.getElementById('video-url').value;
    const resultDiv = document.getElementById('result');

    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: videoUrl, type }),
        });

        const data = await response.json();

        if (response.ok) {
            resultDiv.innerHTML = `<a href="${data.download_link}" class="btn btn-primary" download>Click here to download your ${type}</a>`;
        } else {
            resultDiv.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
        }
    } catch (error) {
        resultDiv.innerHTML = '<p class="text-danger">An error occurred. Please try again later.</p>';
    }
}
