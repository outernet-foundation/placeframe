#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec2;
}

namespace DotNet::CesiumForUnity {

struct CesiumUintVec2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_ooy5yIq__mBEC6X6EtGX5Ow)(::std::uint8_t x, ::std::uint8_t y, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException);
  public: static CesiumUintVec2 Construct(::std::uint8_t x, ::std::uint8_t y);
  private: static void (*Construct_XhEMD4DBm1OQpJbAQjBMWw)(::std::uint16_t x, ::std::uint16_t y, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException);
  public: static CesiumUintVec2 Construct(::std::uint16_t x, ::std::uint16_t y);
  private: static void (*Construct_41DRfMZ91WmKUsGkzEnbPw)(::std::uint32_t x, ::std::uint32_t y, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException);
  public: static CesiumUintVec2 Construct(::std::uint32_t x, ::std::uint32_t y);
  private: static void (*Construct_nrWljXjq__N5wiftR3c_JGg)(::std::uint64_t x, ::std::uint64_t y, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException);
  public: static CesiumUintVec2 Construct(::std::uint64_t x, ::std::uint64_t y);
  private: static ::std::uint64_t (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintVec2* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::uint64_t operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::std::uint64_t x;
  public: ::std::uint64_t y;
};

} // namespace DotNet::CesiumForUnity


