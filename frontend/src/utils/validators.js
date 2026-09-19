export const isValidMssv = (mssv) => /^[0-9A-Z]{6,10}$/.test(mssv?.trim() ?? '')

export const isValidOtp = (otp) => /^[0-9]{6}$/.test(otp?.trim() ?? '')
