#include <DotNet/Unity/Mathematics/double4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double4;
}

namespace DotNet::Unity::Mathematics {

void (*double4::Construct_vGP51u8UcgYZVrSmxERqcw)(double x, double y, double z, double w, ::DotNet::Unity::Mathematics::double4* pReturnValue, void** reinteropException) = nullptr;


double4 double4::Construct(double x, double y, double z, double w)
{
    void* reinteropException = nullptr;
    double4 result;
    Construct_vGP51u8UcgYZVrSmxERqcw(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


double (*DotNet::Unity::Mathematics::double4::Property_get_Item)(const ::DotNet::Unity::Mathematics::double4* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


double double4::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


