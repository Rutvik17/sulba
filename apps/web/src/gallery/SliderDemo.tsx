import { Slider } from '@sulba/ui/slider';

const decays = [0.0001, 0.001, 0.01, 0.1];

/**
 * Sliders in a React island: a fraction, a whole number, one through a list of stops, and one that
 * can't be moved.
 */
export default function SliderDemo() {
  return (
    <>
      <Slider
        label="Learning rate"
        defaultValue={0.1}
        minValue={0}
        maxValue={1}
        step={0.01}
        formatOptions={{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}
      />
      <Slider label="Epochs" defaultValue={20} minValue={1} maxValue={100} />
      <Slider
        label="Weight decay"
        defaultValue={2}
        minValue={0}
        maxValue={decays.length - 1}
        valueText={(index) => String(decays[index])}
      />
      <Slider
        label="Batch size"
        defaultValue={32}
        minValue={8}
        maxValue={256}
        step={8}
        isDisabled
      />
    </>
  );
}
