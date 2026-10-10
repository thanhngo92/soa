import { useState, useEffect, useRef, useCallback } from 'react'

export default function useCountdown(initialSeconds = 300) {
  const [seconds, setSeconds] = useState(0)
  const intervalRef = useRef(null)

  const start = useCallback(() => {
    clearInterval(intervalRef.current)
    setSeconds(initialSeconds)
    intervalRef.current = setInterval(() => {
      setSeconds((s) => {
        if (s <= 1) {
          clearInterval(intervalRef.current)
          return 0
        }
        return s - 1
      })
    }, 1000)
  }, [initialSeconds])

  const reset = useCallback(() => {
    clearInterval(intervalRef.current)
    setSeconds(0)
  }, [])

  useEffect(() => {
    return () => clearInterval(intervalRef.current)
  }, [])

  const mm = String(Math.floor(seconds / 60)).padStart(2, '0')
  const ss = String(seconds % 60).padStart(2, '0')

  return { seconds, display: `${mm}:${ss}`, isActive: seconds > 0, start, reset }
}
