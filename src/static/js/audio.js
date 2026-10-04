/**
 * Audio feedback engine for AISYS using the Web Audio API.
 * Synthesizes exact frequencies for audible confirmation events without external audio files.
 * Fulfills FR 06, FR 07.
 */
class AudioManager {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }

  init() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.ctx = new AudioContext();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playTone(freq, durationMs, type = 'sine') {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

      gain.gain.setValueAtTime(0.15, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + (durationMs / 1000));

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + (durationMs / 1000));
    } catch (e) {
      console.warn("Audio playback not allowed yet:", e);
    }
  }

  // 880Hz single chime: Item verified / Tag encoded / Checkout success
  playSuccessBeep() {
    this.playTone(880, 120, 'sine');
  }

  // 440Hz double pulse: Misplaced item warning
  playWarningDoublePulse() {
    this.playTone(440, 100, 'triangle');
    setTimeout(() => {
      this.playTone(440, 150, 'triangle');
    }, 140);
  }

  // 220Hz persistent buzzer: Security Gate Alarm
  playGateAlarm() {
    this.playTone(220, 600, 'sawtooth');
    setTimeout(() => this.playTone(200, 600, 'sawtooth'), 650);
  }

  // Low buzz: Policy violation or error
  playErrorBuzz() {
    this.playTone(150, 250, 'sawtooth');
  }
}

window.audioManager = new AudioManager();
