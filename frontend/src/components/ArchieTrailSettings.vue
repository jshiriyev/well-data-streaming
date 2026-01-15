<template>
    <div class="settings-panel">
        <div class="settings-row settings-row--split">
            <div class="settings-heading" data-role="trail-title">Trail</div>
            <button class="settings-button settings-button--danger" data-action="clearTrail" type="button">Clear
                curves</button>
        </div>

        <div class="settings-row">
            <label class="settings-field">
                <span class="settings-label" data-role="xmin-label">X min (optional)</span>
                <input class="settings-input" type="number" step="any" placeholder="auto" data-field="xMin"
                    data-role="xmin-input" />
            </label>
            <label class="settings-field">
                <span class="settings-label" data-role="xmax-label">X max (optional)</span>
                <input class="settings-input" type="number" step="any" placeholder="auto" data-field="xMax"
                    data-role="xmax-input" />
            </label>
        </div>

        <div class="settings-section">Curves</div>
        <div class="curve-list"></div>
    </div>
</template>