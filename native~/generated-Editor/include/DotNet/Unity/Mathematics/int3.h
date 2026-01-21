#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct int3;
}

namespace DotNet::Unity::Mathematics {

struct int3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_2lzDmp63Mfw__oFMy0HdgWw)(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::DotNet::Unity::Mathematics::int3* pReturnValue, void** reinteropException);
  public: static int3 Construct(::std::int32_t x, ::std::int32_t y, ::std::int32_t z);
  public: ::std::int32_t x;
  public: ::std::int32_t y;
  public: ::std::int32_t z;
};

} // namespace DotNet::Unity::Mathematics


