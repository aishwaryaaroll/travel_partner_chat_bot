import { stampColor } from '../utils/text';

/** Selectable chips. Single-select calls onChange with one value; multi-select with an array. */
export function ChipSelect({ options, value, multi = false, onChange, disabled = false, label }) {
  const selected = multi ? value || [] : value;
  const isOn = (opt) => (multi ? selected.includes(opt) : selected === opt);

  const toggle = (opt) => {
    if (!multi) return onChange(opt);
    onChange(isOn(opt) ? selected.filter((v) => v !== opt) : [...selected, opt]);
  };

  return (
    <div className="chips" role="group" aria-label={label}>
      {options.map((opt, i) => (
        <button
          key={opt}
          type="button"
          className={`chip ${isOn(opt) ? 'chip--on' : ''}`}
          style={{ '--chip': stampColor(i) }}
          aria-pressed={isOn(opt)}
          disabled={disabled}
          onClick={() => toggle(opt)}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
