import {
  Slider as AriaSlider,
  type SliderProps as AriaSliderProps,
  Label,
  SliderFill,
  SliderOutput,
  SliderThumb,
  SliderTrack,
} from 'react-aria-components/Slider';
import { classes } from '../classes';
import styles from './slider.module.css';

const css = classes(styles, 'slider', 'header', 'label', 'output', 'track', 'fill', 'thumb');

export interface SliderProps
  extends Omit<AriaSliderProps<number>, 'className' | 'style' | 'children'> {
  /** The slider's visible name, such as "Learning rate". */
  label: string;
}

/**
 * A number chosen by dragging, or with the keys: arrows step, Page Up and Page Down take larger
 * steps, and Home and End reach the ends. formatOptions sets how the value is written.
 */
export function Slider({ label, ...props }: SliderProps) {
  return (
    <AriaSlider {...props} className={css.slider}>
      <div className={css.header}>
        <Label className={css.label}>{label}</Label>
        <SliderOutput className={css.output} />
      </div>
      <SliderTrack className={css.track}>
        <SliderFill className={css.fill} />
        <SliderThumb className={css.thumb} />
      </SliderTrack>
    </AriaSlider>
  );
}
