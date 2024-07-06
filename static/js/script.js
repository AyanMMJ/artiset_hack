document.addEventListener('DOMContentLoaded', function () {
    const editor = document.getElementById('editor');
    const outputElement = document.getElementById('output');
    const languageSelector = document.getElementById('language');

    function runCode() {
        const code = editor.value;
        const language = languageSelector.value;

        try {
            fetch('/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code, language })
            })
            .then(response => response.json())
            .then(result => {
                if (result.result !== undefined) {
                    outputElement.textContent = `Result: ${result.result}`;
                } else if (result.error) {
                    outputElement.textContent = `Error: ${result.error}`;
                }
            })
            .catch(err => {
                outputElement.textContent = `Error: ${err}`;
            });
        } catch (err) {
            outputElement.textContent = `Error: ${err}`;
        }
    }

    document.getElementById('run-button').addEventListener('click', runCode);
});
