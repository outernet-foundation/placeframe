#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Collections {
template <typename T0> struct NativeArray1;
}

namespace DotNet::Unity::Collections::LowLevel::Unsafe {

class NativeArrayUnsafeUtility {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: NativeArrayUnsafeUtility() = delete;
  public: template <typename T>
  static void* GetUnsafeBufferPointerWithoutChecks(const ::DotNet::Unity::Collections::NativeArray1<T>& nativeArray);
  private: static void* (*CallGetUnsafeBufferPointerWithoutChecks_QIjAavb5O6M1Tim2Rs2ohQ)(void* nativeArray, void** reinteropException);
  private: static void* (*CallGetUnsafeBufferPointerWithoutChecks_VYRTjxyHQQFS6luUIZqMHQ)(void* nativeArray, void** reinteropException);
  private: static void* (*CallGetUnsafeBufferPointerWithoutChecks_iVtd6RQjrruzXGL_Bo80bw)(void* nativeArray, void** reinteropException);
  private: static void* (*CallGetUnsafeBufferPointerWithoutChecks_Lv3zldnuDkcZt7Gk__iYidg)(void* nativeArray, void** reinteropException);
  private: static void* (*CallGetUnsafeBufferPointerWithoutChecks_dODsb2EbtCXW9Y67cYH1sg)(void* nativeArray, void** reinteropException);
  private: static void* (*CallGetUnsafeBufferPointerWithoutChecks_ExoUtqZSMWnuKvejW2dcYw)(void* nativeArray, void** reinteropException);
};

} // namespace DotNet::Unity::Collections::LowLevel::Unsafe


