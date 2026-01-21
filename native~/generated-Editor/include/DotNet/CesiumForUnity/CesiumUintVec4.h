#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec4;
}

namespace DotNet::CesiumForUnity {

struct CesiumUintVec4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_V8zlQY__7MR4_A1Ek6HBQqg)(::std::uint8_t x, ::std::uint8_t y, ::std::uint8_t z, ::std::uint8_t w, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException);
  public: static CesiumUintVec4 Construct(::std::uint8_t x, ::std::uint8_t y, ::std::uint8_t z, ::std::uint8_t w);
  private: static void (*Construct_yp__VrxlOcxUXq2RwGv8mXw)(::std::uint16_t x, ::std::uint16_t y, ::std::uint16_t z, ::std::uint16_t w, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException);
  public: static CesiumUintVec4 Construct(::std::uint16_t x, ::std::uint16_t y, ::std::uint16_t z, ::std::uint16_t w);
  private: static void (*Construct_cx5C8OyRaFgckdYoG5u6cw)(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::std::uint32_t w, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException);
  public: static CesiumUintVec4 Construct(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::std::uint32_t w);
  private: static void (*Construct_eKggYQNxOSW0_H_SNc53xA)(::std::uint64_t x, ::std::uint64_t y, ::std::uint64_t z, ::std::uint64_t w, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException);
  public: static CesiumUintVec4 Construct(::std::uint64_t x, ::std::uint64_t y, ::std::uint64_t z, ::std::uint64_t w);
  private: static ::std::uint64_t (*Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintVec4* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::uint64_t operator[](::std::int32_t index) const;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: ::std::uint64_t x;
  public: ::std::uint64_t y;
  public: ::std::uint64_t z;
  public: ::std::uint64_t w;
};

} // namespace DotNet::CesiumForUnity


