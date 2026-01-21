#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec3;
}

namespace DotNet::CesiumForUnity {

struct CesiumUintVec3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_jH1j0POYh80kGurO6bbg6w)(::std::uint8_t x, ::std::uint8_t y, ::std::uint8_t z, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException);
  public: static CesiumUintVec3 Construct(::std::uint8_t x, ::std::uint8_t y, ::std::uint8_t z);
  private: static void (*Construct_r71YnkpCpNgMBAJTUEeKlg)(::std::uint16_t x, ::std::uint16_t y, ::std::uint16_t z, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException);
  public: static CesiumUintVec3 Construct(::std::uint16_t x, ::std::uint16_t y, ::std::uint16_t z);
  private: static void (*Construct_fwI58ky8hlqSzCrUJCqq4Q)(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException);
  public: static CesiumUintVec3 Construct(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z);
  private: static void (*Construct_ZbSqyVsWZtDI0Ryj__6S2Iw)(::std::uint64_t x, ::std::uint64_t y, ::std::uint64_t z, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException);
  public: static CesiumUintVec3 Construct(::std::uint64_t x, ::std::uint64_t y, ::std::uint64_t z);
  private: static ::std::uint64_t (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintVec3* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::uint64_t operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::std::uint64_t x;
  public: ::std::uint64_t y;
  public: ::std::uint64_t z;
};

} // namespace DotNet::CesiumForUnity


