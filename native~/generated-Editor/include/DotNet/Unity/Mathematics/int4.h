#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct int4;
}

namespace DotNet::Unity::Mathematics {

struct int4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_ima1GH0lko9R2DnR_aRPyw)(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::std::int32_t w, ::DotNet::Unity::Mathematics::int4* pReturnValue, void** reinteropException);
  public: static int4 Construct(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::std::int32_t w);
  public: ::std::int32_t x;
  public: ::std::int32_t y;
  public: ::std::int32_t z;
  public: ::std::int32_t w;
};

} // namespace DotNet::Unity::Mathematics


